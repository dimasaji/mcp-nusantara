# Audit arsitektur dan integrasi

Kontrak NCP-V1-FULL-PRD-AUDIT-001 / 002. 27 Oktober 2026, Asia/Jakarta.
Baseline: `scripts/NUSANTARA-V1-MASTER-PRD.docx`, versi deklaratif **1.0 Draft**, ditetapkan operator untuk audit melalui jawaban “ya, dijadikan Baseline Audit”. Kontrak arsitektur FINAL berlaku untuk Hermes V1 inti; integrasi Hermes baru dinilai terpisah. Persetujuan baseline bukan approval operasional, handover, atau izin perbaikan.

HEAD `7b6859df6bb912902b34f9a0796b3062239ab350`; working tree lokal ikut diperiksa dan diuji, terpisah dari HEAD. Semua lokasi file:line mengacu working tree saat audit. Laporan ini menggantikan checkpoint HOLD awal; PRD tidak diedit.

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
