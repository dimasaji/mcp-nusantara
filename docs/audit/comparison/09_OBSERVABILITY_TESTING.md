# Fase 8 — Observability, evidence, dan pengujian

Tanggal inspeksi: 2026-10-21, Asia/Jakarta. `OW` berarti `E:/OpenWebUI/.venv/Lib/site-packages/open_webui`; path lain relatif terhadap `C:/Users/dmaza/mcp-starter`. Fakta source di bawah [FAKTA-KODE]; penilaian severity/rekomendasi [INFERENSI].

| Area | Open WebUI (bukti) | Nusantara (bukti) | Status Nusantara | Severity | Rekomendasi | Aksi |
|---|---|---|---|---|---|---|
| Request correlation | OW/utils/auth.py:426 get_current_user menambah atribut span; OW/main.py:585 setup OTEL bersyarat | app/main.py:86 request_id_middleware; app/observability/logging.py:34 JsonFormatter | ADA | LOW | P1 pertahankan request_id; hubungkan ke request chat dan receipt model | KEEP |
| Metrics | OW/main.py:2712 get_current_usage; bukan bukti Prometheus aktif [ASUMSI] | app/observability/metrics.py:9 Metrics, observe:20, snapshot:27; app/api/routes.py:1480 get_metrics | ADA | MEDIUM | P1 bedakan metric proses, HTTP, provider, dan retrieval | ADAPT |
| Health | OW/main.py:3063 healthcheck; :3109 check_db_health | app/main.py:105 health_check; app/api/routes.py:918 health_check mengembalikan HealthResponse; :924 health_detail melakukan probe | SEBAGIAN | MEDIUM | P0 health dasar jangan dijadikan bukti model/RAG siap | ADAPT |
| Logging/redaction | OW/main.py:366 lifespan start_logger:382; format efektif [ASUMSI] | app/observability/logging.py:20 redact; :51 configure_logging hanya logger nusantara | ADA | MEDIUM | P1 pastikan logger semua jalur sensitif memakai redaction dan request_id | ADAPT |
| Dashboard evidence | [ASUMSI] parity dashboard OW tidak diperiksa | app/core/control_plane_projection.py:20 project; runtime_view dan warning historis:129-137; control-plane/src/overview.tsx:28 OverviewPage | SEBAGIAN | HIGH | P1 pertahankan label historical/fixture dan freshness; tambah receipt runtime setelah pengujian sah | KEEP |
| Test collection | [ASUMSI] test suite upstream tidak disertakan sebagai checkout source | tests/test_phase2_hardening.py:11 test_sync_timeout; tests/test_approval_persistence.py:6 test_approval_survives_restart_and_cannot_replay; tests/test_indobert_timeout.py:7 test_hung_worker_is_terminated_and_can_recover; hasil runtime di bawah | SEBAGIAN | HIGH | P0 jangan menyamakan collected dengan PASS, coverage, atau RAG live | KEEP |

## Pengumpulan yang benar-benar dijalankan

[FAKTA-RUNTIME] Perintah berikut dijalankan dari root Nusantara dengan plugin autoload dimatikan dan bytecode/cache dimatikan. Percobaan pertama dibatasi akses interpreter Windows; pengulangan dengan izin baca/eksekusi yang disetujui berhasil, exit code 0.

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONDONTWRITEBYTECODE='1'
& .venv/Scripts/python.exe -B -m pytest --collect-only -p no:cacheprovider -o addopts= tests/test_phase2_hardening.py tests/test_approval_persistence.py tests/test_indobert_timeout.py -q
```

Hasil: **13 tests collected in 0.24s**. Angka 0.24s adalah durasi collection, bukan latensi chat. Warning: `Unknown config option: asyncio_mode`, karena plugin autoload dinonaktifkan. Tidak ada test body dijalankan dan tidak ada klaim PASS.

Node yang terkumpul:

```text
tests/test_phase2_hardening.py::test_sync_timeout
tests/test_phase2_hardening.py::test_sync_timeout_does_not_block_event_loop
tests/test_phase2_hardening.py::test_contextvars_propagate_to_sync_thread
tests/test_phase2_hardening.py::test_sync_function_returning_awaitable
tests/test_phase2_hardening.py::test_sync_function_returning_awaitable_respects_total_timeout
tests/test_phase2_hardening.py::test_async_timeout
tests/test_phase2_hardening.py::test_no_timeout_path
tests/test_phase2_hardening.py::test_safe_exception_handling
tests/test_phase2_hardening.py::test_circuit_breaker_regression
tests/test_phase2_hardening.py::test_circuit_breaker_records_success
tests/test_approval_persistence.py::test_approval_survives_restart_and_cannot_replay
tests/test_approval_persistence.py::test_corrupt_audit_is_not_a_source_of_permission
tests/test_indobert_timeout.py::test_hung_worker_is_terminated_and_can_recover
```

## Cakupan nyata vs klaim

[FAKTA-KODE] PIAK dialog memakai `tests/test_v1_service_dialogue.py:44` setup dengan penggantian search_knowledge; ingestion rollback/idempotency memiliki fungsi test pada `tests/test_sop_ingestion.py:22` pipeline dan :27 test_failed_ingestion_rolls_back_document_and_chunks. UI Vitest dan Playwright dideklarasikan pada `control-plane/package.json:3-5`. Ini bukti struktur unit/contract/integration/UI yang direncanakan; bukan bukti seluruhnya lulus. Test negatif tampak pada `tests/test_v1_service_dialogue.py:37` test_real_model_cannot_add_delivery_steps_or_calendar_facts. Nama test tidak membuktikan memakai model nyata.

[FAKTA-KODE] Collection seluruh tests berisiko mengimpor aplikasi: `tests/evaluation/test_smoke.py:3` dan `tests/test_chat_openrouter_route_wiring_v1.py:9` mengimpor app.main; `app/main.py:17-25` memuat settings/routes di profil normal; `app/api/routes.py:50` membangun KnowledgeEngine; `app/knowledge/store.py:32` SQLiteVectorStore.__init__ menginisialisasi penyimpanan. [INFERENSI] Karena R1/R2 lebih ketat daripada izin collect-only, collection penuh tidak dijalankan. File terpilih ditinjau import-nya sebelum collection. Tidak mengimpor app.main, membaca .env, membuka knowledge DB, atau memulai worker dalam collection terpilih.

[ASUMSI] Total test yang dapat dikoleksi dengan seluruh dependency aktif, statement/branch coverage, hasil regression, e2e UI, ketepatan indeks produksi, dan hubungan dashboard ke proses aktif belum diverifikasi. Tidak ada persentase coverage dihitung dari jumlah file.

## Dashboard benar dalam arti apa?

[FAKTA-KODE] `project` memvalidasi hash artefak dan membaca laporan XML historis (`app/core/control_plane_projection.py:24` nested read; :86-99 verification); runtime diberi scope HISTORICAL_CONTROLLED_RUNTIME dan current_status NOT_VERIFIED (:129-137). UI `OverviewPage` menampilkan waktu pembacaan snapshot dan peringatan (:46-68). [INFERENSI] Ini berguna untuk evidence governance, tetapi waktu pembacaan baru tidak membuat isi artefak lama menjadi bukti perilaku backend baru. Health dan test collection audit ini tidak menggantikan receipt live.

P0 acceptance lanjutan: uji RAG aktif dan uji negatif privacy memakai fixture resmi nonrahasia di lingkungan terisolasi, setelah persetujuan implementasi/pengujian yang menulis state. P1 acceptance: satu request_id dapat ditelusuri UI→API→retrieval→model→final→audit, dengan timestamp dan build/config revision, tanpa teks SOP atau credential dalam log publik. HOLD: jangan menjalankan evaluasi agent otonom untuk menambah angka coverage.
