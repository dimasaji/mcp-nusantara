# Matriks kepatuhan PRD NUSANTARA V1

Kontrak NCP-V1-FULL-PRD-AUDIT-001 / 002. 27 Oktober 2026, Asia/Jakarta.
Baseline: `scripts/NUSANTARA-V1-MASTER-PRD.docx`, versi deklaratif **1.0 Draft**, ditetapkan operator untuk audit melalui jawaban “ya, dijadikan Baseline Audit”. Kontrak arsitektur FINAL berlaku untuk Hermes V1 inti; integrasi Hermes baru dinilai terpisah. Persetujuan baseline bukan approval operasional, handover, atau izin perbaikan.

HEAD `7b6859df6bb912902b34f9a0796b3062239ab350`; working tree lokal ikut diperiksa dan diuji, terpisah dari HEAD. Semua lokasi file:line mengacu working tree saat audit. Laporan ini menggantikan checkpoint HOLD awal; PRD tidak diedit.

## Aturan status dan denominator

PASS berarti acceptance requirement terbukti pada interface/lingkungan yang ditulis; tidak menyatakan deployment produksi PASS. FAIL berarti ada bukti kegagalan, termasuk kontradiksi implementasi statis yang jelas. HOLD berarti bukti/prasyarat operasional belum lengkap. NOT TESTED dipakai untuk subkriteria yang belum dijalankan; bukan sinonim fitur tidak ada. Satu test hijau tidak otomatis meluluskan semua subkriteria.

Total 15 FR: **3 PASS, 6 FAIL, 6 HOLD, 0 NOT TESTED** pada status agregat. Tujuh FR diuji cukup untuk verdict perilaku pada seam yang dicantumkan: FR-03, FR-04, FR-05, FR-06, FR-07, FR-11, FR-14. Kepatuhan teruji **3/7 = 42.86%**; coverage requirement dengan verdict perilaku teruji **7/15 = 46,67%**. FAIL dapat ditetapkan dari satu subkriteria gagal tanpa mengklaim seluruh subkriteria telah dijalankan. Dua FAIL statis (FR-09/10) tidak dimasukkan denominator perilaku; HOLD yang memiliki sebagian tes juga tidak dihitung sebagai FR dengan verdict perilaku konklusif. Ini bukan klaim 42,86% sistem produksi siap.

## Requirement fungsional dari DOCX bagian 5

| ID / acceptance | Status | Cakupan pengujian | Kode dan API | Database, frontend, tes, evidence, batas dan tindak lanjut |
|---|---|---|---|---|
| **FR-01** Chat lokal: 3+ pertanyaan berurutan tanpa reset/500 | **HOLD** | Sebagian; runtime NOT TESTED | `app/api/routes.py:1051`; `app/hermes/agent.py:281`; POST /v1/chat | MemoryEngine/JSON chat-history; assistant.tsx; test_ncp_v1_chat_contract 13 PASS dan selected_pdf_chat 7 PASS; provider fixture. Runtime A-00 menolak koneksi; tiga pertanyaan model lokal nyata belum diuji. |
| **FR-02** OpenRouter dapat dipilih; respons dan usage tercatat | **HOLD** | Sebagian; provider nyata NOT TESTED | `app/api/control_plane.py:113,142`; `app/models/openrouter.py:59,143`; GET models, POST model-selection | Config owner, cost ledger; selector assistant.tsx; test_openrouter_provider memakai MockTransport. Tidak ada panggilan berbayar/key asli; seleksi/generasi nyata belum diuji. |
| **FR-03** Upload PDF, validasi dan identitas konsisten | **FAIL** | Diuji pada HTTP/storage terisolasi | `app/api/knowledge_pipeline.py:113,122`; `app/knowledge/engine.py:230`; POST /knowledge/pipeline/documents | knowledge_pipeline_runs, source-documents SHA-256; KnowledgeOperationsPage/api.ts:71; pipeline_api tes positif/negatif PASS, namun probe A-04 malformed Content-Length HTTP 500. P2: perbaiki validasi/buffering. |
| **FR-04** Docling: teks, halaman, versi, sumber asli tersedia | **PASS** | Diuji native + interface storage terisolasi | `app/knowledge/document_tools.py:103,157`; `app/knowledge/docling_worker.py:11`; POST /reviews/{id}/process; GET source | document_extractions/docling JSON, original SHA-256; sop-review.tsx; native-result COMPLETE 1 halaman/2 blok/0 warning; document_tools 2 PASS, layout/preview tests PASS. Native PDF sintetis; bukan sertifikasi OCR scan/SOP resmi. Integritas approval diuji terpisah FR-05. |
| **FR-05** Operator memeriksa dan menyetujui versi tanpa 500 | **FAIL** | Diuji state machine/HTTP fixture | `app/knowledge/sop_review.py:94,150`; `app/api/knowledge_pipeline.py:39,96`; GET review, POST decision | sop_review_events/trials/sessions/pilots; SOPReviewPanel; review 4 PASS untuk gate existing, tetapi probe A-02 mengubah isi ekstraksi tanpa mengubah approval Aktif. P1. HTTP 500 review historis belum direproduksi, bukan penyebab A-02. |
| **FR-06** Persisten setelah restart; transaksi aman | **PASS** | Diuji fresh interpreter dan transaksi SQLite fixture | `app/knowledge/store.py:61`; `app/knowledge/rag.py:269`; `app/knowledge/engine.py:107` | documents/chunks/pipeline/review/extraction + originals; UI lewat status/review; ingestion_atomic_profiles 4 PASS; reopen-results mencatat proses baru, 1 dokumen, sumber asli, approval/status/ekstraksi tersimpan. Tidak restart service aktif atau menguji power-loss filesystem. |
| **FR-07** Dokumen disetujui terindeks dan dapat ditemukan | **FAIL** | Diuji retrieval/aktivasi terisolasi | `app/knowledge/engine.py:288`; `app/security/v1_knowledge.py:30`; `app/knowledge/rag.py:563` | SQLite canonical Chat, pipeline READY; Knowledge/review UI. A-01: dokumen belum direview dapat diretrieve sebelum enrollment, lalu hilang setelah enrollment. PRD §6 approval-before-operational-index tidak konsisten; P1. |
| **FR-08** Jawaban persyaratan/prosedur/waktu sesuai PDF | **HOLD** | Fixture PASS; SOP/model nyata NOT TESTED | `app/hermes/agent.py:378,478,729`; `app/knowledge/document_answers.py`; POST /v1/chat | Evidence blocks/source pages dan SOP trial; assistant/sop-review; selected_pdf_chat 7 PASS, dialogue/grounding suites; tidak ada oracle SOP resmi/model aktif yang dijalankan pada audit ini. Bukti 9+3 jawaban lama bukan hasil sekarang. |
| **FR-09** Judul resmi dan halaman sumber dapat dibuka | **FAIL** | Kegagalan integrasi UI statis; klik main Chat NOT TESTED | `control-plane/src/assistant.tsx:123`; `control-plane/src/sop-review.tsx:115`; GET /reviews/{id}/source | Original/preview route dan title/page evidence ada serta preview fixture PASS. Main Chat hanya menampilkan metadata tanpa kontrol pembuka halaman (A-06, P2). Pembukaan di panel review tidak membuktikan jalur sitasi main Chat. |
| **FR-10** Control Plane menampilkan status aktual tanpa mock status | **FAIL** | Kegagalan kontrak statis; parity runtime HOLD | `app/api/routes.py:939,990`; `app/api/control_plane.py:62,171,412`; GET /health, model-status, snapshot | Runtime projection dan historical manifests, settings/operator UI. Components detail health konstan available (A-05), health asli hanya liveness. Probe A-00 frontend 200/backend refused/proxy500. Mock UI PASS bukan backend parity. |
| **FR-11** PASS/FAIL/HOLD tersimpan dan tercermin state | **PASS** | Diuji API/log persisten terisolasi | `app/api/control_plane.py:187,256,289`; `app/core/evidence_registry.py:319,364`; POST/GET decisions | Hash-linked evidence_decisions JSONL + checkpoint; Human Control. evidence_decision_api 5 PASS dan registry 12 PASS. Keputusan fixture sintetis, tidak ada approval atau handover operator otomatis. Executor fixture yang membutuhkan git commit diblokir terpisah. |
| **FR-12** Run ID, tes dan artefak terlacak | **HOLD** | Interface registry PASS; binding sumber saat ini bermasalah | `app/knowledge/engine.py:188`; `app/core/evidence_registry.py:94,185`; GET evidence-package | Pipeline runs/manifests/hash-chain; Human/technical evidence UI. Registry 12 PASS; A-08 current-source pin routes.py mismatch dan A-07 graph consumer menolak graph. Paket acceptance revisi lokal belum ditetapkan; jangan mempromosikan laporan lama menjadi bukti aktual. |
| **FR-13** Usage OpenRouter tercatat; limit terkendali | **HOLD** | Caps/ledger fixture PASS; operasional NOT TESTED | `app/models/cost_ledger.py:59,112,171,216`; `app/models/openrouter.py:93,143`; `app/api/routes.py:1211` | cost_policy/cost_reservations; GET cost-summary/CostsPage. cost_ledger 7 PASS, provider mocked; cost-summary recheck 2 PASS. Route memakai budget $1/cap $0.05 fixed; kebijakan limit operator/usage provider aktual belum dibuktikan. |
| **FR-14** Backup terverifikasi; restore/rollback diuji | **FAIL** | Diuji helper backup WAL; recovery penuh NOT TESTED | `app/knowledge/production_kb.py:1012`; `app/developer_core/snapshot_manager.py:194,359` | Backup DB lama dan source snapshots berbeda owner; Settings menyatakan API maintenance belum tersedia. A-03 kehilangan committed WAL row. P1: backup konsisten + restore fixture. Tidak menjalankan restore database/service lokal. |
| **FR-15** Secret aman, akses terlindungi, audit dasar | **HOLD** | Kontrol negatif fixture PASS; readiness keamanan belum lengkap | `app/security/auth.py`; `app/security/v1_knowledge.py:21`; `app/core/evidence_registry.py:364` | Shared operator role, basic hash-linked audit; auth UI. Public knowledge denied dan remote internal-doc provider ditolak pada fixture; .env asli tidak dibaca. A-04 buffering/validation, A-09 retention dan akses runtime belum ditutup. Bukan hasil pentest/deployment publik. |

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
