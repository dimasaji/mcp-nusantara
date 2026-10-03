# CHANGELOG
## 2.0.0-alpha.3
`/v1/chat` live: patch `integration/routes_devcore.patch` mengganti routing hard-code `healthcheck.py` dengan DevCore generik; response menambah key `developer`.
Integrasi: `RegistryBackend` (adapter ke ToolRegistry live), `DevCore.handle_sync`, patch `integration/hermes_agent_devcore.patch` untuk `app/hermes/agent.py`. Gerbang path DevCore berlaku sebelum & sesudah registry live; path absolut POSIX kini diekstrak agar diblokir eksplisit.
Tambah Developer Core (`app/devcore/`, `POST /v2/dev`) sesuai NUSANTARA_AI_DEVELOPER_CORE_WORKFLOW.md & MASTER_ENGINEERING_SKILL.md: tool read-only (read_file/find_file/list_directory) lewat registry governed, ekstraksi referensi file generik, security gate workspace, analisis ter-grounding + pemeriksa klaim, fallback fakta statis AST. Perubahan/eksekusi ditolak (read-only).

## 2.0.0-alpha.2
Tambah Phase 7–21: RAG berversi+konflik+akses, validasi manifest MCP, sandbox allowlist, telemetry event, feedback, evaluasi 10 dimensi + deteksi REGRESSION, failure analysis, gap detection, knowledge discovery (kandidat, wajib approval), experiment, improvement proposal, change request, gerbang V1.x + registri versi, scanner secret, release check, backup/rollback helper. `/v2/feedback`, `/v2/experience/analysis`.

## 2.0.0-alpha
Tambah: hardening, observability, approval+audit trail, tool governance, V2 orchestrator, `/v2/*`, middleware X-Request-ID.
Perbaiki: LongTermMemory (JSON, atomic, anti-traversal), kode mati di PolicyRule.
Tidak berubah: seluruh kontrak `/v1`.
Catatan migrasi: file memory `.pkl` lama tidak dimuat lagi.
