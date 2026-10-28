"""Assemble the eight requested audit reports from recorded evidence."""
import json
import re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'reports/audit'
E=OUT/'evidence'
git=json.loads((E/'git_baseline.json').read_text())
inv=json.loads((E/'source_inventory.json').read_text())
integrity=json.loads((E/'audit-integrity-summary.json').read_text())
head=git['head']['stdout'].strip()
root=git['roots']['stdout'].strip()
baseline=json.loads((E/'prd-baseline.json').read_text(encoding='utf-8-sig'))
stamp='27 Oktober 2026, Asia/Jakarta'
header=f'''Kontrak NCP-V1-FULL-PRD-AUDIT-001 / 002. {stamp}.
Baseline: `scripts/NUSANTARA-V1-MASTER-PRD.docx`, versi deklaratif **1.0 Draft**, ditetapkan operator untuk audit melalui jawaban “ya, dijadikan Baseline Audit”. Kontrak arsitektur FINAL berlaku untuk Hermes V1 inti; integrasi Hermes baru dinilai terpisah. Persetujuan baseline bukan approval operasional, handover, atau izin perbaikan.

HEAD `{head}`; working tree lokal ikut diperiksa dan diuji, terpisah dari HEAD. Semua lokasi file:line mengacu working tree saat audit. Laporan ini menggantikan checkpoint HOLD awal; PRD tidak diedit.
'''

findings=[
('A-00','P1','FR-01/02/08; Reliability; DoD 1/3',
 '`config/local-services.json:2`; `control-plane/vite.config.ts:10`; `evidence/runtime-probe-final.json`',
 'Backend 127.0.0.1:8000 dan Ollama 11434 menolak koneksi; frontend 5180 HTTP 200, proxy /health HTTP 500.',
 'Runtime chat/model dan E2E resmi tidak dapat diuji saat observasi. Penyebab proses tidak tersedia belum diketahui.',
 'Periksa status supervisor/log tersensor dan konfigurasi target. Restart hanya pada fase perbaikan yang disetujui; jangan menyebut frontend HTTP 200 sebagai sistem sehat.'),
('A-01','P1','FR-05/07/11; Integrity; DOCX §6',
 '`app/knowledge/engine.py:250`; `app/knowledge/engine.py:288`; `app/security/v1_knowledge.py:38`; `app/api/knowledge_pipeline.py:44`',
 'Probe A-01: upload READY, review “Menunggu pemeriksaan isi”, retrieval operator=1 sebelum enrollment dan 0 setelah enrollment; tanpa approval.',
 'Dokumen belum diperiksa dapat masuk retrieval operator; membuka review mengubah eligibility. Bukan bukti akses publik karena public boundary tetap menolak.',
 'Tentukan staging/aktivasi pada owner yang ada; daftarkan gate sejak ingest dan terapkan sebelum semua jalur retrieval. Pertahankan jalur uji operator yang eksplisit dan tidak mempromosikan dokumen.'),
('A-02','P1','FR-04/05; Integrity; DoD 2',
 '`app/knowledge/sop_review.py:97`; `app/knowledge/sop_review.py:119`; `app/knowledge/document_tools.py:112`; `app/knowledge/document_tools.py:157`',
 'Probe A-02: dua payload ekstraksi berbeda hash; version_id dan approval tidak berubah, status tetap Aktif. Worker sintetis; state machine/storage asli.',
 'Approval tidak membuktikan identitas isi Docling yang dipakai Chat. Cache key parser/config terpisah dari versi review.',
 'Ikat approval/trial/sitasi pada identitas ekstraksi substantif yang immutable; perubahan isi memerlukan review ulang. Jangan menghapus event historis.'),
('A-03','P1','FR-14; Recoverability; DoD 5',
 '`app/knowledge/production_kb.py:540`; `app/knowledge/production_kb.py:1012`; `app/knowledge/production_embedding_bridge.py:35`; `app/knowledge/official_knowledge_ingestion.py:636`',
 'Probe A-03 menjalankan fungsi backup_database existing hasil ekstraksi AST: sumber WAL berisi 1 committed row, salinan backup berisi 0. Seluruh DB sintetis.',
 'Backup main .db dapat kehilangan committed WAL. Berlaku pada helper production KB lama yang diuji, bukan bukti semua jenis snapshot Nusantara rusak.',
 'Gunakan snapshot SQLite konsisten/online backup pada owner existing; verifikasi integrity dan restore terisolasi, termasuk originals, metadata dan ekstraksi yang diperlukan.'),
('A-04','P2','FR-03; Reliability/Security',
 '`app/api/knowledge_pipeline.py:122`; `app/knowledge/engine.py:234`',
 'Probe HTTP A-04 Content-Length=invalid-length menghasilkan HTTP 500. Source juga membaca request.body() sebelum memeriksa panjang aktual.',
 'Pada seam ASGI TestClient header malformed menjadi error server; listener HTTP dapat menolak lebih awal. Batas 20 MB belum membatasi buffering body tanpa declared length; risiko buffering statis, tanpa stress traffic.',
 'Validasi header sebagai 4xx dan batasi byte selama streaming; pertahankan validasi downstream. Jangan mengubah PRD atau memperlonggar batas untuk meloloskan tes.'),
('A-05','P2','FR-10; Observability',
 '`app/api/routes.py:939`; `app/api/routes.py:990`',
 'Detailed health hanya mem-probe provider, tetapi 12 components diberi string konstan available. Bukti statis; UI/backend parity penuh belum diuji.',
 'Status komponen tidak dibuktikan oleh probe individual. /health hanya liveness dan versi, bukan readiness seluruh sistem.',
 'Pisahkan inventory/liveness/readiness; tampilkan NOT VERIFIED untuk komponen yang belum diprobe dan sertakan waktu/sumber observasi.'),
('A-06','P2','FR-09; Usability; DOCX §6',
 '`control-plane/src/assistant.tsx:123`; `control-plane/src/sop-review.tsx:115`; `control-plane/e2e/main-chat-docling-live.spec.ts:46`',
 'Main Chat merender judul, nomor halaman dan document_id di details tanpa tautan/tombol pembuka sumber. Tombol Buka halaman tersedia di panel SOP Review; live spec main-chat hanya memeriksa metadata halaman.',
 'Sitasi main Chat tidak tersambung ke pembacaan halaman asli. Endpoint preview ada, tetapi keberadaan endpoint bukan bukti UI Chat terhubung.',
 'Hubungkan sitasi Chat ke preview sumber terautentikasi dan versi yang tepat melalui owner existing; uji klik halaman, bukan hanya nomor metadata.'),
('A-07','P2','FR-12; Developer Core; Observability',
 '`app/developer_core/engine.py:89`; `app/developer_core/engine.py:155`; `tests/test_gate14_developer_core.py:40`; `graphify-out/graph.json`',
 'Graph berukuran 65.991.241 byte, melebihi batas consumer 16.777.216 byte; test_gate14_existing_graphify gagal loaded=True. Source menolak sebelum membaca JSON.',
 'Integrasi Graphify -> Developer Core menolak graph existing walau JSON ada. Graph juga memuat backup/snapshot sehingga navigasi harus memverifikasi owner aktif.',
 'Rancang representasi scoped atau mekanisme konsumsi bounded sesuai kontrak; jangan sekadar melepas limit keselamatan atau rebuild arsitektur.'),
('A-08','P2','FR-12; DoD evidence/regression',
 '`tests/v1_baseline.py:19`; `tests/fixtures/v1-current-contract/source-contract.json`; `tests/test_runtime_verification.py:338`',
 'Pin current_sources untuk app/api/routes.py berbeda dari hash working tree; test sumber-terlindungi dan pembandingan kontrak historis gagal. 645 hash source tetap sama sepanjang audit.',
 'Bukti historis tidak otomatis berlaku pada revisi lokal. Kegagalan pin bukan bukti bahwa perubahan source salah secara fungsional.',
 'Review perubahan terhadap acceptance yang berlaku, kemudian buat run evidence baru terikat revisi. Jangan menyesuaikan oracle/pin secara otomatis agar hijau.'),
('A-09','P2','FR-15; Security/data minimization',
 '`app/memory/engine.py:48`; `app/memory/engine.py:133`; `app/memory/engine.py:171`; `docs/contracts/NUSANTARA-CONTROL-PLANE-V1.md`',
 'clear() hanya menghapus sessions; _chat_turns dan JSON persisten tidak dihapus. Tidak ada expiry lintas session pada jalur yang diperiksa. Temuan statis; tidak membaca chat pengguna.',
 'clear bukan penghapusan history persisten; governance memory masih gate terbuka. Multi-user lengkap tetap deferred, bukan requirement baru audit.',
 'Putuskan consent/retention/clear semantics V1 dan uji pada fixture. Jangan menghapus history lokal dalam audit.'),
('A-10','P2','FR-12; Human Control/Observability',
 '`app/api/routes.py:64`; `app/api/routes.py:1527`; `app/handoff/engine.py:20`',
 'POST handoff menggunakan HandoffEngine baru sementara; request hanya disimpan dalam dict instance lalu owner dibuang. Hermes memakai shared _handoff_engine yang berbeda.',
 'ID handoff dari endpoint tidak mempunyai lifecycle pada owner bersama. Ini bukan kegagalan log keputusan Control Plane yang terpisah.',
 'Bila endpoint dimaksud operasional, gunakan owner authoritative dan lifecycle terlacak; dokumentasikan batas handoff versus acceptance decision.'),
('A-11','P3','FR-12; kualitas regresi/Usability',
 '`control-plane/tests/operator.test.tsx:65`; `control-plane/src/assistant.tsx:124`; `tests/test_document_answers.py`',
 'UI test masih mencari Ollama · fixture-local dan gagal serial; test wording biaya mengharapkan “Informasi biaya ...” tetapi respons kini “Biaya ...”. Followup timeout lulus pada pengulangan serial.',
 'Suite mencampur kontrak lama, assertion wording dan kegagalan produk. Satu timeout bukan bukti deterministik bug approval.',
 'Review ekspektasi terhadap baseline; pertahankan assertion makna/safety yang penting, perbarui fixture hanya setelah review. Laporkan flake terpisah.'),
('D-01','P3','FR-12; maintenance/locality',
 '`app/developer_core/controlled_patch_executor.py:113`; `app/developer_core/snapshot_manager.py:178`; `app/api/routes.py:1234`',
 'Helper SHA-256 identik; dua konstruksi HermesAgent berurutan. Inventaris 645 file menemukan 4 grup file identik dan 80 grup function AST identik termasuk salinan backup.',
 'Debt duplikasi/ownership dan kerja konstruktor berulang. Angka bukan 80 bug atau bukti semua salinan digunakan.',
 'Konsolidasikan hanya sesudah approval dan pembuktian caller/recovery ownership. Jangan menghapus backup atau membangun core kedua.'),
('D-02','P3','FR-10/12; dokumentasi arsitektur',
 '`docs/contracts/NUSANTARA-KNOWLEDGE-RAG-CONTRACT-V1.md:8`; `app/knowledge/engine.py:52`; `app/api/routes.py:77`; `pyproject.toml:7`',
 'Kontrak lama menyebut filter ignored/two slots; source menerapkan filter dan sepuluh slot. Metadata package masih 2.0.0a3 sedangkan ruang lingkup produk audit V1.',
 'Nama versi dan dokumen tidak cukup menentukan execution path atau acceptance V1.',
 'Buat addendum implementasi/evidence setelah review; pertahankan sejarah dan PRD baseline. Jangan menjadikan metadata alasan migrasi V2.'),
]

def finding_table():
    return '| ID | Prioritas | Requirement | Lokasi/bukti | Dampak dan rekomendasi |\n|---|---|---|---|---|\n'+''.join(
        f'| {i} | {p} | {req} | {loc}. {proof} | {impact} **Rekomendasi:** {rec} |\n'
        for i,p,req,loc,proof,impact,rec in findings)

fr=[
('FR-01','Chat lokal: 3+ pertanyaan berurutan tanpa reset/500','HOLD','Sebagian; runtime NOT TESTED',
 '`app/api/routes.py:1051`; `app/hermes/agent.py:281`; POST /v1/chat',
 'MemoryEngine/JSON chat-history; assistant.tsx; test_ncp_v1_chat_contract 13 PASS dan selected_pdf_chat 7 PASS; provider fixture. Runtime A-00 menolak koneksi; tiga pertanyaan model lokal nyata belum diuji.'),
('FR-02','OpenRouter dapat dipilih; respons dan usage tercatat','HOLD','Sebagian; provider nyata NOT TESTED',
 '`app/api/control_plane.py:113,142`; `app/models/openrouter.py:59,143`; GET models, POST model-selection',
 'Config owner, cost ledger; selector assistant.tsx; test_openrouter_provider memakai MockTransport. Tidak ada panggilan berbayar/key asli; seleksi/generasi nyata belum diuji.'),
('FR-03','Upload PDF, validasi dan identitas konsisten','FAIL','Diuji pada HTTP/storage terisolasi',
 '`app/api/knowledge_pipeline.py:113,122`; `app/knowledge/engine.py:230`; POST /knowledge/pipeline/documents',
 'knowledge_pipeline_runs, source-documents SHA-256; KnowledgeOperationsPage/api.ts:71; pipeline_api tes positif/negatif PASS, namun probe A-04 malformed Content-Length HTTP 500. P2: perbaiki validasi/buffering.'),
('FR-04','Docling: teks, halaman, versi, sumber asli tersedia','PASS','Diuji native + interface storage terisolasi',
 '`app/knowledge/document_tools.py:103,157`; `app/knowledge/docling_worker.py:11`; POST /reviews/{id}/process; GET source',
 'document_extractions/docling JSON, original SHA-256; sop-review.tsx; native-result COMPLETE 1 halaman/2 blok/0 warning; document_tools 2 PASS, layout/preview tests PASS. Native PDF sintetis; bukan sertifikasi OCR scan/SOP resmi. Integritas approval diuji terpisah FR-05.'),
('FR-05','Operator memeriksa dan menyetujui versi tanpa 500','FAIL','Diuji state machine/HTTP fixture',
 '`app/knowledge/sop_review.py:94,150`; `app/api/knowledge_pipeline.py:39,96`; GET review, POST decision',
 'sop_review_events/trials/sessions/pilots; SOPReviewPanel; review 4 PASS untuk gate existing, tetapi probe A-02 mengubah isi ekstraksi tanpa mengubah approval Aktif. P1. HTTP 500 review historis belum direproduksi, bukan penyebab A-02.'),
('FR-06','Persisten setelah restart; transaksi aman','PASS','Diuji fresh interpreter dan transaksi SQLite fixture',
 '`app/knowledge/store.py:61`; `app/knowledge/rag.py:269`; `app/knowledge/engine.py:107`',
 'documents/chunks/pipeline/review/extraction + originals; UI lewat status/review; ingestion_atomic_profiles 4 PASS; reopen-results mencatat proses baru, 1 dokumen, sumber asli, approval/status/ekstraksi tersimpan. Tidak restart service aktif atau menguji power-loss filesystem.'),
('FR-07','Dokumen disetujui terindeks dan dapat ditemukan','FAIL','Diuji retrieval/aktivasi terisolasi',
 '`app/knowledge/engine.py:288`; `app/security/v1_knowledge.py:30`; `app/knowledge/rag.py:563`',
 'SQLite canonical Chat, pipeline READY; Knowledge/review UI. A-01: dokumen belum direview dapat diretrieve sebelum enrollment, lalu hilang setelah enrollment. PRD §6 approval-before-operational-index tidak konsisten; P1.'),
('FR-08','Jawaban persyaratan/prosedur/waktu sesuai PDF','HOLD','Fixture PASS; SOP/model nyata NOT TESTED',
 '`app/hermes/agent.py:378,478,729`; `app/knowledge/document_answers.py`; POST /v1/chat',
 'Evidence blocks/source pages dan SOP trial; assistant/sop-review; selected_pdf_chat 7 PASS, dialogue/grounding suites; tidak ada oracle SOP resmi/model aktif yang dijalankan pada audit ini. Bukti 9+3 jawaban lama bukan hasil sekarang.'),
('FR-09','Judul resmi dan halaman sumber dapat dibuka','FAIL','Kegagalan integrasi UI statis; klik main Chat NOT TESTED',
 '`control-plane/src/assistant.tsx:123`; `control-plane/src/sop-review.tsx:115`; GET /reviews/{id}/source',
 'Original/preview route dan title/page evidence ada serta preview fixture PASS. Main Chat hanya menampilkan metadata tanpa kontrol pembuka halaman (A-06, P2). Pembukaan di panel review tidak membuktikan jalur sitasi main Chat.'),
('FR-10','Control Plane menampilkan status aktual tanpa mock status','FAIL','Kegagalan kontrak statis; parity runtime HOLD',
 '`app/api/routes.py:939,990`; `app/api/control_plane.py:62,171,412`; GET /health, model-status, snapshot',
 'Runtime projection dan historical manifests, settings/operator UI. Components detail health konstan available (A-05), health asli hanya liveness. Probe A-00 frontend 200/backend refused/proxy500. Mock UI PASS bukan backend parity.'),
('FR-11','PASS/FAIL/HOLD tersimpan dan tercermin state','PASS','Diuji API/log persisten terisolasi',
 '`app/api/control_plane.py:187,256,289`; `app/core/evidence_registry.py:319,364`; POST/GET decisions',
 'Hash-linked evidence_decisions JSONL + checkpoint; Human Control. evidence_decision_api 5 PASS dan registry 12 PASS. Keputusan fixture sintetis, tidak ada approval atau handover operator otomatis. Executor fixture yang membutuhkan git commit diblokir terpisah.'),
('FR-12','Run ID, tes dan artefak terlacak','HOLD','Interface registry PASS; binding sumber saat ini bermasalah',
 '`app/knowledge/engine.py:188`; `app/core/evidence_registry.py:94,185`; GET evidence-package',
 'Pipeline runs/manifests/hash-chain; Human/technical evidence UI. Registry 12 PASS; A-08 current-source pin routes.py mismatch dan A-07 graph consumer menolak graph. Paket acceptance revisi lokal belum ditetapkan; jangan mempromosikan laporan lama menjadi bukti aktual.'),
('FR-13','Usage OpenRouter tercatat; limit terkendali','HOLD','Caps/ledger fixture PASS; operasional NOT TESTED',
 '`app/models/cost_ledger.py:59,112,171,216`; `app/models/openrouter.py:93,143`; `app/api/routes.py:1211`',
 'cost_policy/cost_reservations; GET cost-summary/CostsPage. cost_ledger 7 PASS, provider mocked; cost-summary recheck 2 PASS. Route memakai budget $1/cap $0.05 fixed; kebijakan limit operator/usage provider aktual belum dibuktikan.'),
('FR-14','Backup terverifikasi; restore/rollback diuji','FAIL','Diuji helper backup WAL; recovery penuh NOT TESTED',
 '`app/knowledge/production_kb.py:1012`; `app/developer_core/snapshot_manager.py:194,359`',
 'Backup DB lama dan source snapshots berbeda owner; Settings menyatakan API maintenance belum tersedia. A-03 kehilangan committed WAL row. P1: backup konsisten + restore fixture. Tidak menjalankan restore database/service lokal.'),
('FR-15','Secret aman, akses terlindungi, audit dasar','HOLD','Kontrol negatif fixture PASS; readiness keamanan belum lengkap',
 '`app/security/auth.py`; `app/security/v1_knowledge.py:21`; `app/core/evidence_registry.py:364`',
 'Shared operator role, basic hash-linked audit; auth UI. Public knowledge denied dan remote internal-doc provider ditolak pada fixture; .env asli tidak dibaca. A-04 buffering/validation, A-09 retention dan akses runtime belum ditutup. Bukan hasil pentest/deployment publik.'),
]
statuses=Counter(row[2] for row in fr)
tested_ids=['FR-03','FR-04','FR-05','FR-06','FR-07','FR-11','FR-14']
tested_pass=sum(row[2]=='PASS' and row[0] in tested_ids for row in fr)
percentage=tested_pass/len(tested_ids)*100

matrix='# Matriks kepatuhan PRD NUSANTARA V1\n\n'+header+f'''
## Aturan status dan denominator

PASS berarti acceptance requirement terbukti pada interface/lingkungan yang ditulis; tidak menyatakan deployment produksi PASS. FAIL berarti ada bukti kegagalan, termasuk kontradiksi implementasi statis yang jelas. HOLD berarti bukti/prasyarat operasional belum lengkap. NOT TESTED dipakai untuk subkriteria yang belum dijalankan; bukan sinonim fitur tidak ada. Satu test hijau tidak otomatis meluluskan semua subkriteria.

Total 15 FR: **{statuses['PASS']} PASS, {statuses['FAIL']} FAIL, {statuses['HOLD']} HOLD, 0 NOT TESTED** pada status agregat. Tujuh FR diuji cukup untuk verdict perilaku pada seam yang dicantumkan: {', '.join(tested_ids)}. Kepatuhan teruji **{tested_pass}/7 = {percentage:.2f}%**; coverage requirement dengan verdict perilaku teruji **7/15 = 46,67%**. FAIL dapat ditetapkan dari satu subkriteria gagal tanpa mengklaim seluruh subkriteria telah dijalankan. Dua FAIL statis (FR-09/10) tidak dimasukkan denominator perilaku; HOLD yang memiliki sebagian tes juga tidak dihitung sebagai FR dengan verdict perilaku konklusif. Ini bukan klaim 42,86% sistem produksi siap.

## Requirement fungsional dari DOCX bagian 5

| ID / acceptance | Status | Cakupan pengujian | Kode dan API | Database, frontend, tes, evidence, batas dan tindak lanjut |
|---|---|---|---|---|
'''+''.join(f'| **{i}** {title} | **{status}** | {coverage} | {code} | {detail} |\n' for i,title,status,coverage,code,detail in fr)+'''
## Requirement nonfungsional DOCX bagian 9

| ID audit / requirement | Status | Pemetaan dan evidence | Dampak/prioritas/rekomendasi |
|---|---|---|---|
| NFR-R Reliability: normal tanpa 500, error mempunyai pesan/trace | FAIL | pipeline.py:122, routes error projection; A-04 HTTP 500; A-00 proxy500; fixture errors/timeouts sebagian PASS | P2 validasi; P1 runtime availability. Review500 historis tetap HOLD |
| NFR-I Integrity: approval versi, persist/index konsisten | FAIL | sop_review.py:97; document_tools.py:112; probes A-01/A-02; transaksi dan reopen PASS | P1 ikat aktivasi/ekstraksi; pertahankan audit log |
| NFR-G Grounding: sumber dan pengakuan di luar sumber | HOLD | Hermes/document_answers/grounding; selected_pdf_chat/ncp tests PASS; wording test berbeda; SOP resmi/model nyata NOT TESTED | P1 oracle persyaratan/prosedur/waktu/biaya/missing setelah runtime siap |
| NFR-U Usability: operator nonteknis dapat menyelesaikan workflow | HOLD | router.tsx/operator.tsx/assistant.tsx/sop-review.tsx; browser 3 PASS mock API; A-06 sumber Chat belum terhubung | P2 uji klik sumber dan uji operator nyata; jangan menyintesis handover |
| NFR-S Security: API key aman, data rahasia tidak keluar tanpa izin | HOLD | auth.py/v1_knowledge.py/openrouter; negative tests fixture PASS; A-04/A-09; tidak membaca .env asli atau melakukan paid request | P1/P2 gate sebelum penggunaan lebih luas; tidak menambah requirement multi-user deferred |
| NFR-O Observability: log/status/biaya/evidence terlacak | FAIL | registry/ledger fixture PASS; health components konstan, graph_limit, pin sumber tidak cocok A-05/A-07/A-08 | P2 status terukur dan evidence per revisi |
| NFR-X Recoverability: backup/restore sebelum deployment | FAIL | production backup source dan A-03, helper snapshot berbeda dari full-data recovery | P1 online backup + restore/recovery terisolasi |

## Kelengkapan inventaris modul DOCX bagian 4

| Modul baseline | Status audit | Pemetaan aktual dan batas |
|---|---|---|
| Core Engine | HOLD runtime | FastAPI main.py/routes.py/core config; SQL transaction dan fixture API diuji, backend target tidak reachable |
| Chat & Models | HOLD operasional | Hermes/providers/router/gateway + assistant; local/OpenRouter fixtures, tanpa model nyata aktif |
| Knowledge & RAG | FAIL gate | canonical SQLiteVectorStore/RAG/engine, IndoBERT dimension768 fixture; A-01; native embedding inference NOT TESTED |
| Document Intelligence | FAIL integritas review | Docling native extraction PASS; SOPReview dan A-02; review500 asli HOLD |
| Control Plane | FAIL status/sitasi statis | api/control_plane.py dan React views, health constants A-05; parity live HOLD |
| Developer Core R1–R21 | FAIL integrasi graph; closure HOLD | developer_core/engine.py/runtime.py/graph_bridge.py; A-07/A-08; tidak mengklaim semua R1–R21 lulus |
| Tools & Skills/workflow | HOLD kesiapan operasional | governance/tools.py, execution/, mcp/, workflow/v1_langgraph.py; fixture/policy tests saja; tidak mengeksekusi tindakan nyata yang menulis sistem |
| Hermes | Core HOLD runtime; integrasi baru HOLD/deferred | app/hermes/agent.py tetap V1; ACP connection-only tidak dianggap task-execution PASS |
| Maintenance | FAIL backup; recovery penuh HOLD | source snapshot berbeda dari DB recovery; A-03; service scripts dibaca, tidak menjalankan update/restart/restore |
| Security | HOLD readiness | auth, local-knowledge boundary, ledger/audit; tes negatif sebagian PASS; tanpa pentest publik atau membuka secrets |

## Persyaratan lintas bagian dan Definition of Done

| Lokasi PRD / kewajiban | Status | Pemetaan, evidence dan batas |
|---|---|---|
| §1 satu SOP Disdukcapil end-to-end; universal workspace | HOLD | FR-03–09; fixture staged/native extraction teruji, SOP resmi lintas seluruh jalur belum diuji |
| §2 operator-first; R1–R21 internal | HOLD | Main sidebar Chat/Pengaturan; technical views tersedia; snapshot/evidence historis tidak boleh disamarkan sebagai live. Uji operator nyata belum ada |
| §2 V1 only, pertahankan FastAPI, tanpa replacement/rebuild | PASS untuk batas tindakan audit | Tidak mengubah source; existing /v2 extension tidak dikembangkan/dihapus. Metadata package V2 bukan izin V2 |
| §2 model lokal/OpenRouter, dokumen sensitif tidak otomatis eksternal | HOLD agregat | Boundary operator knowledge lokal diuji negatif; runtime model nyata belum diuji; FR-02/15 |
| §2 PASS hanya evidence; §12 inventaris read-only | PASS untuk laporan audit | Semua verdict terikat file/run; guard mencegah akses SQL aktif, efek keluar run, subprocess dan jaringan aplikasi. Tidak ada PRD versi baru dibuat karena larangan eksplisit operator |
| §3 empat peran pengguna/operator/developer/admin | HOLD | assistant/operator/settings/evidence ada; kemampuan tersedia dipetakan FR, usability/handover belum diuji dengan orang sebenarnya |
| §4 Hermes inti vs integrasi Agent Workspace baru | Inti HOLD runtime; integrasi baru HOLD/deferred | HermesAgent.execute_v1 terhubung di source dan fixture; ACP connection-only, task_execution_enabled=False; bukan core pengganti |
| §6 upload→Docling→review→approval→save→index→retrieve→chat→sitasi→evidence | FAIL | Ingest memakai ekstraksi awal pypdf dan active index sebelum review; Docling eksplisit terpisah; A-01/A-02/A-06. Bukan kegagalan seluruh primitive storage |
| §6 Permohonan Data Pribadi: persyaratan/prosedur/waktu/biaya jika ada/out-of-source | HOLD | Artefak lama 9+3 jawaban; audit sekarang hanya fixture. Tidak mengarang oracle dari hasil model |
| §7 insiden review HTTP500; identitas SHA-256 konsisten | HOLD insiden | Tidak direproduksi pada data asli; SHA-256/version/source binding fixture diuji. A-04 adalah HTTP500 upload berbeda, jangan disamakan |
| §8 Beranda/AI Workspace/Human Control/Pengaturan & Teknis | HOLD kesesuaian UX | Area tersedia lewat router/settings; top-level Chat/Pengaturan berbeda dari empat menu target. Tiga browser fixture responsif PASS, belum penerimaan operator atas seluruh workflow |
| §10 roadmap P0–P4 dan deferred list | HOLD readiness | Tidak menaikkan deferred menjadi fitur wajib. Remediation diprioritaskan P0–P3 sesuai kontrak audit, bukan mengedit urutan PRD |
| DoD-1 satu SOP upload→jawaban bersitasi, konsisten setelah restart | HOLD | Persistensi fixture lintas interpreter PASS; SOP/model/UI/approval end-to-end nyata belum PASS |
| DoD-2 review/approval tanpa error; keputusan tersimpan | FAIL | Primitive review/decisions persisten PASS; A-02 approval versi isi tidak memadai; insiden historis belum direproduksi |
| DoD-3 lokal dan OpenRouter sesuai konfigurasi/batas keamanan | HOLD | Adapters/cost/negative fixtures PASS; layanan model nyata tidak tersedia, tidak ada paid test |
| DoD-4 status nyata dan evidence valid | FAIL | A-05 availability konstan, A-07 graph_limit, A-08 pin evidence mismatch; tidak ada paket current acceptance lengkap |
| DoD-5 backup/restore/security/regression relevan PASS | FAIL | A-03 backup kehilangan WAL, suite belum hijau; security lengkap HOLD |
| DoD-6 handover disetujui operator; item belum lulus HOLD/FAIL | HOLD | Tidak ada handover atau operational approval dibuat. Persetujuan baseline saja sudah dicatat |

Setiap temuan, dampak, prioritas dan rekomendasi lengkap terdapat dalam [register](TECHNICAL_DEBT_REGISTER.md). Pemetaan independen rinci: [Spec](evidence/spec_findings.md). Semua hasil tes yang disebut dapat ditelusuri pada [laporan pengujian](END_TO_END_TEST_REPORT.md).
'''

history=[]
for line in git['history']['stdout'].splitlines():
    if re.match(r'^[0-9a-f]{40}\|',line):
        sha,parents,date,subject=line.split('|',3)
        history.append({'sha':sha,'parents':parents,'date':date,'subject':subject,'files':0,'adds':0,'deletes':0})
    elif history and re.match(r'^(\d+|-)\t(\d+|-)\t',line):
        adds,deletes,name=line.split('\t',2); history[-1]['files']+=1
        history[-1]['adds']+=int(adds) if adds.isdigit() else 0
        history[-1]['deletes']+=int(deletes) if deletes.isdigit() else 0
tracked=git['tracked_status']['stdout'].strip().splitlines()
untracked=git['untracked']['stdout'].splitlines()
gitreport='# Audit riwayat Git\n\n'+header+f'''
## Jangkauan yang tersedia

Root reachable `{root}`, HEAD `{head}`, **59 commit**, `is-shallow-repository=false`. Root paling awal adalah checkpoint 1 Oktober 2026, bukan bukti proyek benar-benar dimulai di sana. Tidak mengambil remote, checkout, reset, bisect, commit, push atau menjalankan hook. Sejarah sebelum root dan branch yang tidak reachable dari HEAD tidak tercakup; permintaan “sejak commit paling awal yang tersedia” dijawab pada lineage HEAD.

Root→HEAD: {git['root_to_head_stat']['stdout'].strip()}. Angka mencakup dokumen/graph/scripts, bukan hanya kode runtime. Metadata setiap commit dan numstat tersimpan pada [git_baseline.json](evidence/git_baseline.json). Ini audit metadata/timeline seluruh commit dan review perubahan arsitektur/modul terarah; bukan klaim setiap baris pada 207 ribu penambahan telah dibaca manual.

Working tree baseline: **{len(tracked)} tracked files berubah** dan **{len(untracked)} path untracked yang dapat dilist Git**, termasuk source/tests/evidence/PRD lokal. Akses sejumlah direktori dibatasi; angka untracked bukan inventaris sempurna seluruh filesystem. SHA-256 atas 645 source/doc/config/test file diperiksa lagi: **0 drift selama audit**. Semua hasil test berlaku pada working tree dengan hash tersebut, bukan otomatis pada HEAD murni. PRD yang dipakai belum merupakan kontrak final yang disahkan dalam sejarah Git; otoritas baseline berasal dari keputusan operator sesi ini.

## Perubahan arsitektur yang dapat ditelusuri

| Periode/commit | Perubahan yang terlihat dari Git dan source | Implikasi audit |
|---|---|---|
| 91609c8, 1 Oktober | checkpoint Knowledge sebelum RAG validation | Root sudah berisi implementasi; jangan menyatakan initial design lengkap diketahui |
| 3 Oktober, baseline hingga Gate14–16 | runtime graph, change-planning, approval, snapshot/rollback dan controlled executor | Gate presence bukan bukti runtime Chat memakai seluruh gate |
| 5 Oktober | auth/IndoBERT cache, container hardening, V2 boundaries, audit reports | Snapshot evidence lama harus dibatasi revisi/lingkungan; V2 tidak dikembangkan dalam audit |
| 089e6e1–8f86bed, 7 Oktober | developer control, compatible gateway/executor boundaries, configuration/model identity checkpoints | Owner config, loaded identity, invocation evidence dan model availability berbeda makna |
| c260cea/bc41aca/54d0643, 19 Oktober | backend health UI + regression tests | Tes fixture tidak membuktikan service/model live saat ini |
| fe47e90, 20 Oktober | snapshot WIP termasuk pipeline/UI | Fitur telah disimpan sebagai WIP; jangan mengartikan pesan commit sebagai acceptance |
| c3daa79/6d92295, 22 Oktober | Chat menjadi beranda; Control Plane di Pengaturan | Target empat area PRD perlu dibandingkan dengan UI nested, bukan asumsi sidebar empat item |
| a8a341b/a06ac0d, 22 Oktober | checkpoint local repairs dan merge origin | Ada dua lineage dan merge; tiga-dot root→HEAD menangkap reachable evolution, working diff terpisah |
| 7b6859d, 26 Oktober | alignment local source/remote, pipeline/Docling/current boundaries | PRD bertanggal sesudah/seputar alignment tetap Draft; audit current behavior diperlukan |

## Daftar semua commit reachable

Numstat merge dapat kosong tanpa `-m`; angka file bukan diff semantik merge. Tabel mengikuti reverse traversal Git, bukan urutan kalender sempurna pada branch paralel.

| Commit | Tanggal | Parent | File numstat | + / - | Pesan |
|---|---|---|---:|---:|---|
'''+''.join(f"| `{h['sha'][:7]}` | {h['date']} | {h['parents'][:15]} | {h['files']} | {h['adds']} / {h['deletes']} | {h['subject'].replace('|','/')} |\n" for h in history)+'''
## Working tree yang memengaruhi hasil

```text
'''+git['tracked_status']['stdout']+'''
```

Temuan A-08 (FR-12, P2): hash pin current-source routes.py tidak cocok, jadi tes/evidence historis tidak dapat dinyatakan current. Dampak: release evidence belum terikat revisi lokal. Rekomendasi: review perubahan lalu run baru dengan hash; tidak otomatis memperbarui pin. D-01/D-02 (P3) membahas backup copies dan drift dokumentasi; tidak ada otorisasi penghapusan.

Nama file secret dalam daftar Git bukan nilai secret. Audit tidak membaca isi `.env`, menampilkan token/key, atau melakukan secret retrieval dari remote.
'''

architecture='# Audit arsitektur dan integrasi\n\n'+header+'''
## Owner aktual dan jalur penting

`app/main.py` mempertahankan FastAPI, existing `/v1`, serta `/v2` extension existing pada NORMAL profile. Evidence-only/ATTESTATION mempunyai jalur terbatas. Tidak membuat engine baru. Chat runtime membangun HermesAgent lalu memanggil execute_v1; keberadaan modul lain tidak otomatis membuktikan tersambung ke jalur ini. Kontrak FINAL menetapkan `app/hermes/agent.py` sebagai core; Agent Workspace/ACP baru bukan penggantinya.

| Area | Implementasi/interface | Data/caller dan hasil audit |
|---|---|---|
| Boot/config/runtime | main.py:17–25, core/config.py:43, nusantara_config.py | snapshot compose-once/CAS model selector; import NORMAL dapat menginisialisasi store, sehingga full app import dijaga |
| API/Chat | api/routes.py:1051,1131,1234; /v1/chat dan history | Auth→audience/session→knowledge boundary→Hermes→provider→projection; user history persisten; dua konstruktor Hermes berturut-turut D-01 |
| Hermes V1 | hermes/agent.py:281 execute_v1 | language/problem/reasoning/knowledge/gates/trust/grounding/provider; fixtures direct execute nyata, constructor/native models sebagian diganti fixture |
| Language/semantic | language/engine.py, language/semantic/indobert_client.py | Worker IndoBERT/Laya/timeout terpisah; dimension checks fixture PASS; inference IndoBERT aktual belum dibuktikan pada audit |
| Model local/cloud | models/ollama.py, openrouter.py, router.py, gateway.py | Per-request identity dan explicit provider; cloud transport mocked; layanan lokal tidak reachable saat probe |
| Ingest canonical | knowledge/engine.py:143,230,288 | PDF upload memakai pypdf/native extraction awal, menyimpan source dan langsung ingest; bukan otomatis Docling; READY bukan approval |
| Docling | document_tools.py:103–165; docling_worker.py:11 | Proses eksplisit `.venv-docling`, cache berdasarkan parser/config, original source immutable; native offline synthetic COMPLETE; approval identity A-02 |
| Review | sop_review.py:51,94,150; api/knowledge_pipeline.py | Event/trial/rating/version; GET enrollment/DDL dan lease updates punya efek; tidak dipanggil ke database aktif |
| RAG/store | knowledge/rag.py:241,269,563; store.py:61 | SQLite documents/chunks, explicit BEGIN IMMEDIATE/nested savepoint; transaksi fixture PASS; approved-only retrieval gate A-01 |
| Selected document context | security/v1_knowledge.py:30; document_tools.py:173; document_context.py | Local authenticated operator; explicit SOP trial can read before approval tanpa promosi; un-enrolled generic path bermasalah |
| Jawaban/sitasi | document_answers.py, grounding.py, routes projection | Facts/table provenance/absence guards; source blocks/pages; main Chat metadata-only source UI A-06 |
| Control Plane API | api/control_plane.py | model-status/models/selection, cost-summary, snapshot, evidence-package, decisions, execution/history; beberapa data historis berlabel, parity live belum diuji |
| Frontend | router.tsx, assistant.tsx, overview.tsx, sop-review.tsx, operator.tsx, settings.tsx, human.tsx | React/Vite; Chat/Pengaturan sidebar, technical areas nested; component fixtures 186/188 initial; browser mock 3 PASS; A-06 dan stale UI expectation |
| Human approval/evidence | core/evidence_registry.py; approval/runtime_authorization.py | Hash-linked decisions, payload/source binding; actual operator gate tidak disintesis; audit hanya fixture keputusan |
| Tools/MCP | governance/tools.py, tools/, execution/, mcp/ | Existing governed registry dan permission/policy adapter; beberapa registry berbeda peran. Tidak menjalankan tool yang menulis sistem atau arbitrary shell |
| Hermes baru/ACP | hermes ACP connection paths, tests/test_hermes_acp_connection.py | Identity handshake/connection-only; task_execution_enabled=False; tugas→eksekusi→evidence live HOLD/deferred, bukan missing Hermes V1 |
| Developer Core | developer_core/engine.py, graph_bridge.py, runtime.py | Consumer batas 16 MiB menolak graph ~66 MB A-07; R1–R21 nama/status tidak membuktikan closure semua gate |
| Snapshot/recovery | developer_core/snapshot_manager.py, controlled_patch_executor.py | Source snapshot/rollback berbeda dari full knowledge DB+original+extraction recovery; legacy copy2 WAL backup A-03 |
| Alternate knowledge/legacy | knowledge/production_kb.py, production_embedding_bridge.py, official_knowledge_ingestion.py; app/rag; root sop_parser_v* | Path eksperimental/historis berbeda; jangan menyamakan data/knowledge/production_knowledge.db dengan canonical Chat store. Tidak memigrasikan/menyatukan owner |
| Memory/handoff | memory/engine.py, core/gate_integration.py, handoff/engine.py | Persistent history retention open; temporary endpoint owner A-09/A-10 |
| Security/observability | security/auth.py, v1_knowledge.py, observability/, exceptions.py | Fail-closed local knowledge; sanitized public error/usage models; detailed components status statis A-05; tidak ada pentest live |
| Service/container | service/local-services.ps1, supervisor, nusantara-service.ps1; Dockerfile/compose | Config current 8000/5180/11434; read-only health probe membuktikan ketidaksediaan backend/model; Docker/VPS/restart tidak dijalankan |

## Database dan konsistensi

Schema dibaca dari source dan dijalankan pada DB audit baru; database operasional tidak dibuka dengan SQLite. Canonical tables: documents/chunks (`store.py:93,105`), knowledge_pipeline_runs/config (`engine.py:116,123`), sop_review_events/trials/sessions/pilots (`sop_review.py:56–65`), document_extractions (`document_tools.py:32`). Cost policy/reservations berada pada ledger terpisah (`cost_ledger.py:69,77`). Review dan extraction memakai koneksi pipeline beside store, sehingga readiness lintas tabel bukan satu transaksi global. Positif: nested transaction rollback diuji; negatif: aktivasi dan versi ekstraksi tidak memiliki invariant menyeluruh A-01/A-02.

Workflow aktual: upload→source retention→ekstraksi awal pypdf→RAG index→READY; lalu operator review/enroll→Docling eksplisit→trials/ratings→approval. PRD §6 menghendaki review/approval sebelum penyimpanan/index operasional. Staging internal mungkin diperlukan, tetapi saat ini eligibility retrieval un-enrolled terbukti terbuka untuk operator. Status authority UNVERIFIED tidak sama dengan gate aktivasi.

## Cakupan inspeksi dan kode tidak terpakai

Inventaris hash/AST mencakup 645 file pada app, frontend src, tests, scripts, service dan config; 229 file Python app parse tanpa error menurut reviewer Standards. Static decorators terinventaris 59; bukan daftar installed route karena opsional/backup ikut terhitung. Empat grup file dan 80 grup function AST identik adalah kandidat duplikasi, bukan bukti runtime ganda. `.before_*.py`, root parser v2–v5, snapshots, perbaikanbukti dan nested upstream adalah kandidat legacy/unreferenced yang perlu bukti caller/dynamic import/CLI/recovery sebelum disebut dead atau dihapus. Tidak ada daftar “aman dihapus” pada audit ini.

Boundary terputus terkonfirmasi: source-index ke review gate A-01; approval ke extraction content identity A-02; main Chat citation ke source preview A-06 (statis); graph file ke bounded Developer Core A-07; endpoint handoff ke shared owner A-10 (statis). ACP task integration adalah deferred, bukan bug core yang harus direbuild.

## Dokumen dan review

PRD DOCX dibaca lengkap melalui XML read-only; MD ringkasan, repo map, development principles/workflow, architecture decisions/current/target/gap, serta kontrak Architecture/Runtime/Agent/Knowledge/Trust/Model/Tools/Control Plane menjadi referensi. Dokumen historis dapat tertinggal (D-02). Detail review independen ada pada [Standards](evidence/standards_findings.md) dan [Spec](evidence/spec_findings.md); masing-masing tujuh dan lima temuan statis, tidak dijumlahkan sebagai dua belas bug unik karena overlap.

Workflow Nusantara: Graphify query dicoba dan gagal uv trampoline; fallback graph read-only mengorientasi owner lalu source diverifikasi. Diagnosing Bugs menghasilkan empat loop reproduksi sintetis A-01–04. TDD red→green dan refactor **dilewati dengan alasan audit melarang perbaikan**; harness hanya mengukur interface yang diminta operator, tidak menambah test produksi. Codebase Design dipakai menilai locality/owner, tanpa implementasi. Code Review dua agen independen selesai. Graphify update tidak dijalankan karena kode tidak berubah dan audit read-only.

### Standards

Reviewer independen menemukan tujuh temuan statis: enrollment setelah upload mengubah retrieval; approval tidak mengikat Docling content identity; copy mainDB mengabaikan WAL; memory clear/retention belum lengkap; handoff memakai owner sementara; upload buffering/header tidak aman; dokumentasi runtime tertinggal. Duplikasi SHA helper dicatat sebagai heuristic tambahan. Terburuk pada sumbu ini: integritas gate dan binding A-01/A-02. Laporan beserta aturan repo dan bukti lengkap dipertahankan terpisah di standards_findings.md; hasil statis bukan klaim seluruhnya direproduksi reviewer.

### Spec

Reviewer independen menemukan lima gap: urutan index sebelum approval; versi review tidak mencakup ekstraksi; GET review/status menulis state; components health konstan; integrasi ACP hanya connection sementara Hermes core tetap ada. Temuan ACP berstatus HOLD/deferred sesuai scope, bukan kewajiban rebuild. Terburuk pada sumbu ini: PRD approval-before-activation dan approval versi isi tidak terpenuhi. Pemetaan FR/NFR/DoD lengkap dipertahankan terpisah di spec_findings.md. Temuan kedua sumbu overlap; tujuh dan lima tidak dijumlahkan menjadi dua belas bug unik.
'''

testreport='# Laporan pengujian dan end-to-end\n\n'+header+'''
## Bukti saat ini dan perintah

Semua run di `reports/audit/evidence/`. Guard audit menolak SQLite di luar run, pembacaan dotenv kredensial lokal, write di luar run (kecuali perangkat NUL nonpersisten Windows), proses anak/OS command dan koneksi aplikasi. Socketpair internal asyncio Windows diizinkan. Layer dotenv repository diganti kosong sintetis hanya di harness; file asli tidak disentuh. Konfigurasi runtime ini berbeda dari produksi dan dinyatakan pada setiap verdict. Test fixture dapat membuat approve/PASS sintetis pada DB baru; tidak ada operational approval, PASS release, atau handover manusia.

| Run / evidence | Perintah ringkas dari root (Node dari managed runtime) | Hasil | Interpretasi |
|---|---|---|---|
| backend-verified/junit.xml, console, backend-verified-summary.json | `.venv/Scripts/python.exe -B reports/audit/evidence/runner-verified-snapshot.py reports/audit/evidence/backend-verified tests --continue-on-collection-errors --ignore=tests/v2` | exit 1; 1040 PASS, 44 failure, 21 skipped, 47 error; 72,48 s | Seluruh suite V1 yang terkoleksi dicoba dengan snapshot guard final. Dari 91 failure/error, 85 terkait guard; bukan 91 bug. Dua belas error adalah collection errors; jangan menyebutnya seluruh tes dieksekusi |
| backend-final/junit.xml | Runner sama, 17 file terpilih; file tepat tercatat dalam console/XML | exit 1; 169 PASS, 4 failure, 16 error; 21,84 s | Sebelum perbaikan parsing file URI pada guard; 19 blocked subprocess, 1 cost response tersamarkan guard |
| backend-cost-recheck/junit.xml | Runner dengan target `tests/test_cost_summary_api.py` dan run baru | exit 0; 2 PASS | Cost KeyError awal disebabkan guard menganggap SQLite file URI di luar run; normalisasi URI harness memperbaikinya tanpa edit produk |
| frontend-results.json | `node node_modules/vitest/vitest.mjs run --reporter=json --outputFile=../reports/audit/evidence/frontend-results.json` (cwd control-plane) | exit 1; 186 PASS /188, 2 FAIL | 44 suite nodes dari Vitest bukan 44 file unik. API di-mock/fixture; tidak membuktikan backend live |
| frontend-recheck.json | Target operator-followup/operator dengan `--maxWorkers=1 --testTimeout=15000` | exit 1; 14 PASS, 1 FAIL | Timeout save PASS awal tidak berulang serial; mismatch model label tetap gagal |
| browser-results.json, browser-console.txt | `node control-plane/node_modules/@playwright/test/cli.js test --config=reports/audit/evidence/playwright.audit.config.mjs` | exit 0; 3 PASS, 34,5 s | Server audit 5197, existing chat-settings spec width1280/390/320, seluruh API diintercept fixture; bukan E2E backend/model |
| typescript.txt | `node node_modules/typescript/bin/tsc --noEmit` (cwd control-plane) | exit 0 | Tidak membangun/menimpa dist |
| docling-native-final/native-result.json + extraction.json | Env `NUSANTARA_AUDIT_NATIVE_DOCLING=1`; `.venv-docling/Scripts/python.exe -B` runner dengan output run dan PDF audit | exit 0; COMPLETE, 1 halaman, 2 blok, 0 warning | Installed Docling/model lokal benar-benar dijalankan, offline, PDF teks sintetis. Bukan scan OCR atau SOP resmi/multi-page native inference |
| reproductions-final/probe-results.json | Env `NUSANTARA_AUDIT_PROBES=1`; runner pada run reproductions-final | exit 0 harness; empat verdict FAIL perilaku | Fixture valid PDF, judul pilot persis PERMOHONAN DATA PRIBADI. Exit0 berarti pengukuran selesai; A-01–04 adalah kegagalan acceptance. A-04 pada ASGI TestClient, bukan exploit listener live |
| reproductions/reopen-results.json | Env `NUSANTARA_AUDIT_REOPEN=1`; proses Python baru pada fixture yang sama | exit 0; dokumen1/original/approval/extraction persisted | Restart interpreter/storage, bukan restart service aktif |
| runtime-probe-final.json | GET health8000, HTML5180, health proxy5180, Ollama api/version11434 | backend/model ConnectionRefused; HTML200; proxy500 | Observasi UTC 2026-10-27 03:17:17–03:17:21 (10:17 WIB), tanpa token atau endpoint mutating GET |

Awal discovery gagal Git di PATH, CLI graphify uv trampoline, dan Python sandbox. Managed Git/Python dengan izin eksekusi menyelesaikan akses tooling. Run backend-focused awal terhenti karena pembacaan dotenv ditolak; backend-safe terpengaruh socketpair guard. Semua console awal dipertahankan sebagai setup evidence, bukan bug produk. Initial browser config path salah diperbaiki hanya di harness audit; hasil final tiga PASS.

## Klasifikasi sisa kegagalan backend

Run awal backend-expanded: 1039 PASS/45 failure/47 error/21 skipped, tujuh OTHER. Cost-summary KeyError terselesaikan normalisasi URI pada guard dan lulus run verified; tidak ada edit produk. **Enam hasil final OTHER**: (1) wording biaya “Informasi biaya ...” vs “Biaya ...”, mismatch assertion bukan fakta biaya yang salah; (2) graph consumer loaded=False, penyebab ukuran65.991.241 >16.777.216 byte terkonfirmasi A-07; (3) historical public schema comparison berbeda; (4) current-source routes.py hash pin berbeda A-08; (5) unknown-file-descriptor runner test OSError, interaksi runner/capture belum didiagnosis penuh; (6) live-harness CLI expected exit0 got2, belum dipastikan independen guard. Jangan menghitung nomor5/6 sebagai akar bug produk tanpa reproduksi lebih kecil. Detail per test tersimpan backend-verified-summary.json; backend-summary.json mempertahankan run awal.

85 hasil bertanda guard mencakup import NORMAL app yang mencoba DB aktif, subprocess/worker/identity checks, fixture Git prepare yang membuat commit, dan write di luar run. Guard dipertahankan; tidak melakukan fixture Git commit karena larangan operator. Tidak ada suite V2 dijalankan; bukan klaim V2 sehat.

## Alur end-to-end dan batas bukti

| Alur wajib | Hasil audit | Bukti/batas |
|---|---|---|
| PDF→Docling→teks/halaman | PASS komponen native sintetis; HOLD SOP resmi lengkap | Native installed worker output + document_tools/layout/preview fixtures. Direct worker di harness, transport subprocess produksi tidak diuji end-to-end |
| Operator review→approval→save | FAIL invariant versi; primitive persist PASS | A-02 plus sop_review4PASS dan decision API5PASS. Semua keputusan sintetis, bukan approval operator |
| Knowledge→index→retrieval | FAIL approval-before-retrieval | A-01 operator boundary actual, fixture vector dimension3; IndoBERT real inference belum diuji |
| Chat utama→SOP→sumber | HOLD runtime/semantik resmi; FAIL wiring sumber statis | model/backend offline; selected-PDF fixture7PASS; main Chat source card tanpa kontrol preview A-06 |
| Hermes V1→engine→jawaban/evidence | PASS interface fixture; HOLD native/local model | execute_v1 dipanggil nyata dengan provider/language fixture; bukan pengganti V1 |
| Hermes integrasi baru→tugas→eksekusi→evidence | HOLD/deferred | ACP connection-only; tidak menjalankan tugas baru atau mengubah scope PRD |
| Control Plane→status→approval→audit | PASS log keputusan fixture; FAIL komponen status statis; HOLD parity live | registry12PASS, API5PASS, health constants A-05, no actual backend comparison |
| Backup→restore→rollback | FAIL helper WAL; full recovery NOT TESTED | Existing AST-extracted backup kehilangan committed row; tidak restore DB lokal atau menjalankan rollback produksi |
| Satu SOP resmi seluruh jalur setelah service restart | HOLD / NOT TESTED penuh | Diperlukan backend/model aktif, oracle resmi, keputusan operator; tidak dilakukan restart agar data lokal tetap aman |

## Historis bukan hasil saat ini

`artifacts/document-chat-20261023/tests.xml`: 109 cases, 0 failure/error, 2 skipped. `artifacts/v1-execution/regression-final.xml`: 473 cases, 0 failure/error, 17 skipped. `artifacts/docling-ui/answers.json` menyimpan9 jawaban; `artifacts/docling-main-chat/answers.json` menyimpan3. Hash dan lokasi dicatat pada audit-integrity-summary.json. Angka disarikan dari artefak lama; asal proses/provider, source revision dan validitas otoritas SOP belum disahkan untuk HEAD/working tree ini. Tidak dijumlahkan dengan tes audit menjadi “total PASS produk”.

Insiden 26 Oktober “ekstraksi COMPLETE, review HTTP500” pada PRD adalah laporan historis. Audit tidak memanggil review GET aktif karena endpoint menulis enrollment/DDL/lease. HTTP500 malformed upload A-04 dan proxy health500 saat backend refused adalah insiden berbeda. Akar review500 historis tetap HOLD.

Tidak dijalankan: reprocessing PDF operasional, auto-approval, paid OpenRouter, live chat yang menulis history, watchdog scan, backup/restore database aktif, service restart, Docker/VPS deployment, destructive load test, commit/push. Semua batas tersebut mencegah klaim PASS penuh, bukan alasan mengubah requirement.
'''

rca='# Analisis akar masalah\n\n'+header+'''
## Penyebab yang berhasil dibuktikan

Empat loop reproduksi ada pada `evidence/reproduce_findings.py`, dijalankan melalui guard dan menghasilkan `evidence/reproductions-final/probe-results.json`. Input berupa PDF valid/teks/database baru sintetis dan judul pilot yang sama dengan target PRD. Expected result berasal dari PRD (approval sebelum retrieval, approval mengikat isi, backup membawa committed state, invalid input ditolak aman), bukan dari nilai yang dihasilkan implementasi. Tidak ada fix atau siklus green dipaksakan. Probe upload malformed pada seam ASGI TestClient; listener HTTP riil mungkin menolak header sebelum masuk aplikasi.

| ID / requirement / prioritas | Gejala terukur | Mekanisme penyebab dan lokasi | Batas diagnosis / rekomendasi |
|---|---|---|---|
| A-01 / FR-05/07, Integrity / P1 | Belum direview, retrieval1; setelah enrollment retrieval0 | engine.py:288 mengindeks sebelum SOP enrollment; v1_knowledge.py:38/51 hanya mengharuskan Aktif bila is_pilot; review GET pipeline.py:44 menambahkan membership | Terbukti operator-local path, bukan public exposure. Tetapkan staging/activation invariant pada owner existing |
| A-02 / FR-04/05, Integrity / P1 | Hash blok berubah 010b7472…→68a23acb…; versi/approval sama, Aktif | sop_review.py:97 hash tidak menyertakan Docling payload/parser/config/job; document_tools.py:112 cache key berubah sendiri; latest extraction dipakai tanpa rebind approval | Worker output sintetis, actual review/extraction storage methods. Native Docling diuji terpisah; jangan mengklaim parser native tertentu menghasilkan perubahan ini. Ikat approved content identity |
| A-03 / FR-14 / P1 | Source1 committed row, backup0 | backup_database production_kb.py:1012 hanya shutil.copy2(main .db); WAL menyimpan committed row yang tidak masuk salinan | Existing helper diekstrak AST agar owner production tidak diimpor. Bukan bukti data pengguna benar-benar hilang. Gunakan consistent SQLite snapshot + restore verification |
| A-04 / FR-03, Reliability / P2 | Header Content-Length nonnumerik→HTTP500 | knowledge_pipeline.py:122 int() tanpa validasi header; ValueError keluar sebagai server error. Body actual-size check baru setelah request.body() | Reproduksi small synthetic HTTP; unbounded chunked memory risk hanya statis. Validasi4xx dan streaming bound |
| A-07 / FR-12, Developer Core / P2 | Existing-graph test loaded=True gagal | engine.py:89 batas16MiB; graph.json65.991.241B; _load_graph:155 menolak dengan graph_limit sebelum JSON | Fails closed sesuai guard consumer, integrasi artifact tidak memenuhi batas. Gunakan scoped artifact/consumer design, bukan melepas safety limit |
| A-08 / FR-12 / P2 | current-source hash test routes.py gagal | source-contract expected hash tidak sama working source; hash source tidak berubah selama audit | Evidence stale versus revisi lokal, bukan otomatis bug perilaku Chat. Review diff dan jalankan evidence baru |

Source approval masih mengikat trial/rating dan review event IDs; ini kontrol positif. Masalah A-02 adalah identitas isi ekstraksi yang tidak masuk binding, bukan tidak ada binding sama sekali. Canonical transaction/savepoint lulus; A-01 bukan diagnosis korupsi SQLite.

## Akar yang belum dapat ditetapkan

Review HTTP500 SOP asli: **HOLD**. PRD melaporkan insiden, tetapi tidak ada request/stack trace saat ini dari jalur yang sama. GET review aktif mempunyai write side effects, sehingga tidak dipakai sebagai probe read-only. Token, IndoBERT, transaction lock, parser, schema drift dan UI tidak ditetapkan sebagai penyebab tanpa reproduksi. A-04 upload500 tidak menjelaskan review500. Langkah berikut setelah keputusan operator: salinan konsisten/sintetis yang mereproduksi isi/schema relevan; jalankan request identik, capture correlation ID dan exception tersensor, lalu minimisasi satu variabel per eksperimen.

Runtime backend/model absent A-00: ConnectionRefused dibuktikan, tetapi mengapa proses tidak berjalan/port berbeda belum diketahui. Proxy /health500 adalah bukti jalur layanan gagal, bukan bukti insiden review. Jangan mengubah service/config atau restart otomatis selama audit.

A-05 constants, A-06 citation UI, A-09 memory dan A-10 handoff adalah temuan source dengan mekanisme jelas, tetapi belum seluruhnya diuji pada UI/runtime asli; status evidencenya tidak dinaikkan menjadi reproduksi live. Wording/model-label regression adalah mismatch kontrak tes; descriptor/live-harness failures belum diisolasi penuh.

## Model perbaikan yang diusulkan

Pusatkan invariant pada owner existing: eligibility dokumen ditentukan state eksplisit sejak ingest; identitas sumber asli berbeda dari identitas ekstraksi yang direview; approval dan citasi mengikat identitas yang benar; snapshots menggunakan transaksi/storage mechanism yang konsisten; UI menampilkan status berdasarkan evidence. Ini usulan untuk review operator, bukan perubahan arsitektur yang telah dilakukan.
'''

debt='# Register technical debt dan temuan\n\n'+header+'''
P0 = blocker kritis/kerusakan luas/rahasia yang sudah terbukti; **tidak ada P0 terkonfirmasi**. P1 = blocker integritas/operasional utama sebelum readiness; P2 = reliability/integrasi/observability/keamanan terbatas; P3 = maintenance/dokumentasi/quality. Roadmap PRD menyebut workflow “P0”; itu urutan produk, bukan otomatis severity P0 setiap bug.

Status evidence: A-01–04 reproduksi terisolasi; A-00 runtime health observation; A-07 test+source/ukuran; A-08 test+hash; A-05/06/09/10 dan D-01/02 terutama statis; A-11 test/triage. Tidak ada perbaikan atau penghapusan dilaksanakan.

'''+finding_table()+'''
## Duplikasi, kode tidak terpakai dan ownership

Detail hash/AST pada [source_inventory.json](evidence/source_inventory.json). Duplikasi function mencakup salinan `.before_authority_patch.py`, `.before_metadata_authority_patch.py`, dan `.before_authority_hydration.py`; function identik bukan bukti caller aktif ganda. Helper SHA-256 di executor/snapshot adalah heuristic Duplicated Code. Registry di tools/base.py, tools/registry.py, governance/tools.py berbeda role; jangan menyatakan semuanya duplikat atau policy bypass hanya karena nama.

Root parser versions, backup directories, app_backup_before_openrouter, perbaikanbukti, upstream copy dan snapshot adalah kandidat tidak terpakai yang belum dibuktikan aman dihapus. Audit mencatat **dead code operasional yang terbukti aman dihapus: belum ada**. Sebaliknya integrasi A-01/A-02/A-06/A-07/A-10 mempunyai lokasi dan dampak tertentu yang bisa ditindaklanjuti tanpa menghapus modul.

H-01 pada checkpoint awal **resolved oleh keputusan baseline operator**, bukan lagi finding P1. Keterbatasan akses directory tetap dicatat; tooling Git/Python tersedia dengan izin eksekusi, sedangkan graphify CLI masih gagal. Jangan menghitung keterbatasan tooling sebagai defect produk tambahan.
'''

plan='# Rencana remediasi untuk persetujuan operator\n\n'+header+'''
**Tidak ada item di bawah telah dilaksanakan atau diotorisasi sebagai perbaikan.** Audit berhenti setelah laporan. Operator perlu menyetujui scope perbaikan, fixture/target dan tindakan layanan secara konkret; persetujuan baseline sebelumnya tidak mencakup restart, restore, commit atau push.

| Urutan | Prioritas / temuan / requirement | Perbaikan minimum pada V1 existing | Bukti penerimaan yang wajib sebelum PASS |
|---|---|---|---|
| 0 | P0 contingency | Tidak ada P0 terkonfirmasi. Jika kebocoran/korupsi nyata ditemukan, hentikan efek lanjut dan minta keputusan untuk containment spesifik | Bukti tersensor dan dampak terukur; tidak mengarang P0 untuk membenarkan rebuild |
| 1 | P1 A-00; FR-01/02/08 | Investigasi read-only supervisor/target port/log; buat rencana start/restart spesifik untuk approval operator | Backend/model readiness observable; bedakan liveness, model inventory dan generation; tidak mengubah local DB |
| 2 | P1 A-01; FR-05/07 | Terapkan staging/review eligibility sejak ingest pada owner existing; pertahankan explicit operator trial, cegah aktivasi otomatis | Dokumen baru belum approved tidak masuk retrieval biasa; trial terikat doc/version tidak mempromosikan state; approved doc retrievable; GET inspection tidak mengubah eligibility |
| 3 | P1 A-02; FR-04/05 | Tentukan extraction-content identity immutable; ikat review/trial/approval/evidence/citation sesuai identitas; reprocessing berbeda isi memerlukan fresh review | Ubah parser/config/payload menghasilkan invalidation sesuai invariant; approval lama tidak aktif untuk isi baru; history tetap lengkap; source asli SHA-256 tidak berubah |
| 4 | P1 A-03; FR-14 | Ganti copy mainDB dengan backup SQLite konsisten; tentukan cakupan DB/original/extraction/config metadata untuk recovery | Probe WAL1→backup1; integrity_check dan restore pada target baru; rollback source berbeda dari data recovery; tidak menyentuh DB lokal aktif |
| 5 | P2 A-04; FR-03/15 | Header parser aman + bound streaming upload | Missing/malformed/negative/oversized lengths memberi respons4xx tepat; batas byte dipatuhi sebelum buffering besar; small valid/duplicate PDF tetap lulus |
| 6 | P2 A-05/A-06; FR-09/10 | Status komponen berdasar probe/NOT VERIFIED; hubungkan sumber main Chat ke authenticated version-bound preview | Backend offline tidak dilabel tersedia; klik judul/halaman membuka original benar tanpa token dalam URL/log; mobile/desktop berfungsi |
| 7 | P2 A-07/A-08; FR-12 | Pertahankan bounded Developer Core; tetapkan scoped graph dan current evidence source binding setelah review | Existing current graph representation dapat dipakai dalam limit; paket evidence sesuai hash/revisi; invalid/old evidence tetap gagal tertutup |
| 8 | P2 A-09/A-10; FR-12/15 | Operator menetapkan memory consent/retention/clear semantics; satukan handoff lifecycle pada owner yang berlaku bila operasional | Fixture clear/expiry sesuai kontrak; request handoff retained/tracked; tidak menghapus chat pengguna tanpa keputusan |
| 9 | P2/P3 FR-13 + A-11/D-01/D-02 | Putuskan kontrol limit operator dengan scope/lifetime; review stale fixture/wording; konsolidasi duplikasi dan addendum dokumen hanya bila perlu | Limit enforced termasuk unknown reservations; test oracle independen; fixture tidak sekadar disesuaikan agar hijau; tidak ada core kedua |

## Urutan verifikasi setelah perubahan disetujui

Ikuti Graphify→Diagnosing Bugs→TDD→Codebase Design→Code Review. Gunakan acceptance seams yang diminta operator: pipeline API/storage, review version gate, retrieval, Chat/citation, Control Plane/decision audit. Tulis test regresi bermakna untuk temuan yang direproduksi sebelum fix; baseline red harus menangkap bug asli, bukan setup guard. Jalankan regression relevan, kemudian full V1 suite terisolasi dan type/browser checks. Pembaruan graph hanya setelah source benar-benar berubah dan diizinkan scope.

Final operational gate: satu SOP resmi berotoritas/jurisdiksi/tanggal berlaku yang telah diperiksa operator; PDF→Docling→review→approval manusia→persist/index→retrieval→main Chat→sumber dapat dibuka; tanya persyaratan/prosedur/waktu/biaya jika ada dan out-of-source; tiga+ giliran; fresh process/restart terencana pada target aman; local model dan OpenRouter hanya dalam scope izin data/biaya; evidence package current; backup/restore teruji; operator handover nyata. Approval diperlukan untuk tindakan aktual, tidak boleh digantikan keputusan fixture.

Hermes V1 tetap core. Agent Workspace/ACP baru, V2, autonomous developer agent, multi-user penuh, OPD lain dan deployment publik tetap deferred. Jangan mengubah PRD agar mengikuti kegagalan implementasi. Commit/push tetap memerlukan persetujuan terpisah.
'''

executive='# Ringkasan eksekutif audit NUSANTARA V1\n\n'+header+f'''
## Keputusan audit

**Readiness/handover V1: HOLD.** Audit dokumen, riwayat reachable, inventaris source, review dua sumbu, pengujian aman dan rencana remediasi telah diserahkan. E2E SOP resmi pada runtime aktif belum memenuhi gate penerimaan. Hasil HOLD/NOT TESTED dinyatakan eksplisit; laporan bukan sertifikat seluruh kode atau produksi PASS.

Lima belas FR dipetakan ke kode/API/storage/UI/test/evidence; tujuh NFR dan enam DoD serta prinsip/UI/E2E lintas bagian dipetakan pada matriks. Status FR agregat: **3 PASS, 6 FAIL, 6 HOLD**. Tujuh FR diuji cukup untuk verdict perilaku pada seam yang dicatat: **3/7 = 42,86% kepatuhan teruji**, dengan **7/15 = 46,67% coverage requirement dengan verdict perilaku teruji**. FAIL dapat didasarkan satu subkriteria gagal; bukan klaim seluruh subkriteria sudah dijalankan. FR-09/10 FAIL berdasarkan integrasi/source statis dan tidak masuk denominator tujuh; tes parsial/fixtures pada FR HOLD tidak dianggap requirement dengan verdict perilaku konklusif. Angka ini bukan persentase readiness produksi. PASS FR-04/06/11 terbatas pada native PDF sintetis, storage lintas interpreter dan API keputusan terisolasi yang benar-benar diuji.

## Masalah utama dan penyebab

| Temuan | Bukti/dampak | Prioritas dan urutan perbaikan |
|---|---|---|
| A-00 runtime tidak tersedia | backend8000/model11434 ConnectionRefused; frontend5180 HTTP200/proxyhealth500 | P1 investigasi layanan/target sebelum uji operasional; alasan proses tidak tersedia belum diketahui |
| A-01 approval-before-retrieval terputus | Belum direview dapat diretrieve1; setelah enrollment0. Gate hanya berlaku untuk pilot yang telah terdaftar | P1 state staging/aktivasi sejak ingest, tanpa rebuild |
| A-02 approval tidak mengikat isi Docling | Dua hash ekstraksi berbeda, versi/approval tetap sama dan Aktif | P1 immutable extraction identity dan review ulang saat isi berubah |
| A-03 backup mainDB kehilangan WAL | Source1 committed row, backup0 pada existing helper dalam fixture | P1 backup konsisten dan restore terisolasi |
| A-04 invalid upload header HTTP500 | Content-Length nonnumerik melalui route nyata terisolasi | P2 validasi4xx/batas streaming |
| A-05/06 status dan sitasi belum lengkap | Status12 komponen konstan; sumber main Chat hanya metadata tanpa kontrol pembuka | P2 probe jujur dan wiring source preview versi tepat |
| A-07/08 evidence current terhambat | Graph65.991.241B > consumer16MiB; pin routes.py tidak cocok source lokal | P2 scoped bounded graph dan evidence baru setelah review |

A-01–04 direproduksi pada database/PDF baru sintetis; tidak mengubah data pengguna. HTTP500 review SOP asli yang dilaporkan PRD **belum direproduksi** dan akar penyebabnya tetap HOLD. HTTP500 upload dan proxy adalah kasus berbeda. Tidak ada P0 terkonfirmasi. Memory retention, handoff owner, fixture drift, duplikasi dan dokumentasi tercatat P2/P3 dalam register lengkap.

## Pengujian aktual versus sejarah

- Backend V1 final: **1040 lulus, 44 failure, 21 skipped, 47 error**; 85 failure/error berhubungan guard audit. Tidak boleh disebut 91 bug produk. Run awal1039PASS mempunyai satu failure cost-summary akibat guard URI, yang lulus recheck2PASS dan run final tanpa edit produk; enam hasil non-guard final diklasifikasi dalam laporan tes.
- Frontend komponen: **186/188 PASS** pada run lengkap; serial recheck14PASS/1FAIL menunjukkan satu timeout tidak berulang, satu assertion label lama tetap gagal.
- Browser fixture responsive: **3 PASS**; TypeScript `--noEmit`: **PASS**. Bukan backend/model E2E.
- Docling terpasang offline: **COMPLETE, 1 halaman, 2 blok, tanpa warning** pada PDF teks sintetis. Fresh interpreter membuka ulang dokumen/original/approval/extraction fixture: **PASS**.
- Artefak lama109 dan473 test cases, serta9+3 jawaban tersimpan, dipertahankan sebagai historis. Tidak membuktikan hasil runtime saat ini atau seluruh requirement teruji.

## Integritas pekerjaan dan batas

Git tersedia dari root `{root[:7]}` (checkpoint1Oktober) sampai HEAD `{head[:7]}` (26Oktober), **59 commit**, non-shallow. Ada11 tracked file berubah sebelum audit; working tree yang diuji dihash. **645 file diperiksa ulang, nol source drift selama audit**. Riwayat sebelum root dan manual review setiap baris bukan klaim audit ini. Inventaris/AST luas dan inspeksi owner/interface terarah melengkapi review independen Standards/Spec.

Baseline DOCX SHA-256 `{baseline['sha256']}`. PRD tetap berstatus deklaratif Draft tetapi sah sebagai baseline audit berdasarkan keputusan operator; Hermes V1 inti mengikuti kontrak FINAL, integrasi Hermes baru connection-only/deferred. Tidak membuat PRD baru, refactor, rebuild, perubahan source/database aktif, operational approval, service restart, commit atau push. Penulisan hanya laporan/harness/cache/fixture di `reports/audit/`; guard tidak dianggap production sandbox sempurna.

Pekerjaan berhenti setelah laporan. Perbaikan dan tindakan layanan menunggu keputusan operator atas [rencana remediasi](REMEDIATION_PLAN.md).

## Berkas serah terima

1. [Matriks kepatuhan](PRD_COMPLIANCE_MATRIX.md)
2. [Riwayat Git](GIT_HISTORY_AUDIT.md)
3. [Arsitektur](ARCHITECTURE_AUDIT.md)
4. [Pengujian end-to-end](END_TO_END_TEST_REPORT.md)
5. [Akar masalah](ROOT_CAUSE_ANALYSIS.md)
6. [Technical debt](TECHNICAL_DEBT_REGISTER.md)
7. [Rencana perbaikan](REMEDIATION_PLAN.md)
8. [Evidence terukur](evidence/COMMANDS.md)
'''

reports={'PRD_COMPLIANCE_MATRIX.md':matrix,'GIT_HISTORY_AUDIT.md':gitreport,
 'ARCHITECTURE_AUDIT.md':architecture,'END_TO_END_TEST_REPORT.md':testreport,
 'ROOT_CAUSE_ANALYSIS.md':rca,'TECHNICAL_DEBT_REGISTER.md':debt,
 'REMEDIATION_PLAN.md':plan,'EXECUTIVE_AUDIT_SUMMARY.md':executive}
for name,content in reports.items():
    (OUT/name).write_text(content,encoding='utf-8')
print(json.dumps({'reports':list(reports),'requirements':len(fr),'status_counts':dict(statuses),
                  'conclusive_behavior_verdicts':tested_ids,'tested_pass_percent':percentage,'commits':len(history)}))
