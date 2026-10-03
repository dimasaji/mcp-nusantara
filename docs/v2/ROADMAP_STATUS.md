# ROADMAP_STATUS — Phase 0–21 (V2.0.0-alpha.2)

Verifikasi: `python -m unittest tests.v2.test_v2_core tests.v2.test_phases_7_21` (56 tes, stdlib saja, lulus) dan `python scripts/release_check.py`.
Legenda: **Selesai** = kode + tes lulus di sandbox. **Sebagian** = ada yang belum. Tidak ada phase yang telah diuji terhadap V1 sungguhan atau lewat HTTP.

| Phase | Status | Modul | Yang belum |
|---|---|---|---|
| 0 Discovery | Selesai (statis) | PROJECT_BASELINE.md, RISK_REGISTER.md | V1 tidak bisa dijalankan di sandbox |
| 1 Architecture | Selesai | docs/architecture/TARGET_ARCHITECTURE.md | — |
| 2 Hardening | Sebagian | `app/core/hardening/` | belum dipasang ke provider/route V1; timeout thread tidak membunuh fungsi macet |
| 3 Observability | Sebagian | `app/observability/` | token usage, trace, retensi log, dashboard |
| 4 Trust | Sebagian | adapter ke TrustEngine V1 | provenance/source trust per sumber |
| 5 Policy | Sebagian | PolicyEngine V1 + audit hash-chain | modul `permissions` terpisah |
| 6 Memory | Sebagian | perbaikan keamanan LTM (JSON) | governance (what/why/how long), episodic, vector, memory_manager |
| **7 RAG** | **Selesai (inti)** | `app/rag/` | ingest parser file (PDF/docx), embedding nyata, reranker model; belum menggantikan `app/knowledge` V1 |
| **8 MCP** | **Sebagian** | `app/governance/mcp_bridge.py` | belum terhubung ke `MCPServer`/client MCP nyata; hanya validasi manifest + tool bawaan |
| **9 Tool governance** | **Selesai (inti)** | `governance/tools.py`, `sandbox.py` | sandbox = allowlist + timeout, bukan isolasi OS/container |
| **10 Experience** | **Selesai (inti)** | `app/experience/events.py` | analytics/dashboard |
| **11 Feedback** | **Selesai** | `app/experience/feedback.py` | UI feedback |
| **12 Evaluation** | **Sebagian** | `app/evaluation/` | baseline V1 ASLI belum ditangkap; dataset baru 4 kasus smoke; groundedness/relevance heuristik leksikal |
| **13 Failure analysis** | **Selesai (inti)** | `research/failure_analysis.py` | korelasi lintas request, klasifikasi berbasis log tak terstruktur |
| **14 Gap detection** | **Selesai (inti)** | `research/gap_detection.py` | `confidence` heuristik, bukan terkalibrasi |
| **15 Knowledge discovery** | **Sebagian** | `research/knowledge_discovery.py` | tidak mengambil dari jaringan (konten disuplai pemanggil); promosi wajib approval |
| **16 Experiment** | **Selesai (inti)** | `research/experiments.py` | tidak ada penjadwal/dataset besar |
| **17 Improvement proposal** | **Selesai** | `research/improvement.py` | — |
| **18 Human approval** | **Selesai (inti)** | `approval/queue.py`, `change_request.py`, endpoint `/v2/approvals/*` | UI review; autentikasi hanya admin-token |
| **19 V1.x development** | **Sebagian** | `improvement/gate.py` | tidak menjalankan git; hanya validasi syarat + registri versi |
| **20 Regression + security** | **Sebagian** | `security/`, `scripts/release_check.py` | 5 check NOT_RUN (lihat laporan) |
| **21 Release + rollback** | **Sebagian** | `improvement/release.py` | tidak melakukan deploy; tidak ada rilis yang pernah dijalankan |

## Status rilis
`RELEASE_READINESS_REPORT.md` = **CONDITIONAL** (bukan PASS). Tidak ada check FAIL; 5 check NOT_RUN: API test, regresi V1 (`run_tests.py`), auth endpoint, benchmark vs baseline V1, performance.
`POST_RELEASE_REPORT.md` sengaja tidak dibuat: belum ada rilis.

## Yang wajib Anda jalankan di mesin dengan dependensi
1. `pip install -e ".[dev]"` → `python run_tests.py` (baseline V1) → `python scripts/release_check.py` (check 3 akan ikut berjalan).
2. Ganti `system()` di `scripts/run_eval.py` agar memanggil `/v1/chat`, jalankan, simpan sebagai baseline V1 asli.
3. `uvicorn app.main:app` lalu uji `/v1/chat`, `/v2/chat`, `/v2/feedback`, `/v2/experience/analysis`, `/v2/approvals/*` (set `NUSANTARA_ADMIN_TOKEN`).
