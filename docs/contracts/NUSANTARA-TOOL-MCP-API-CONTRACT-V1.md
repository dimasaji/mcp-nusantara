# NUSANTARA V1 — Tool MCP API

Tanggal: 2026-10-06. Status: DOCUMENTED_IMPLEMENTATION_WITH_OPEN_GATES.

Scope: V1; subordinate pada Architecture Contract, Verification Work Contract dan GATES existing. Dokumen ini menutup kekurangan dokumen, bukan bukti acceptance runtime.

## Implementasi dan boundary
`app/mcp/stdio_server.py` memakai official FastMCP stdio sebagai adapter ke `app/governance/tools.py::GovernedToolRegistry`. Expose calculator dan current_time_utc; role user dan permissions kosong ditentukan server, bukan client. Error wire disanitasi; detail masuk audit `audit/mcp.jsonl` di data directory. `app/mcp/mcp.py` adalah facade sederhana dan bukan pengganti transport governed; tidak dipromosikan menjadi jalur privileged.

Registry memeriksa nama terdaftar, permission, policy, input schema, approval terikat tool+args, safe_call/circuit breaker, output schema dan audit. Default policy: critical DENY; high/DELETE/EXECUTE REQUIRE_HUMAN; WRITE/EXTERNAL/medium REQUIRE_CONFIRMATION; read/low ALLOW. ToolSpec timeout default 10 detik. Tidak mengubah policy atau memberi permission baru.

## API dan bukti
`/v1` tetap compatibility boundary, ingest privileged dilindungi admin existing. MCP stdio integration recovery 1 PASS membuktikan transport/tool terdaftar pada lingkungan itu; tidak membuktikan semua modul tools terhubung ke chat atau production authorization lengkap. Test schema/error/permission/approval tetap wajib. Symlink escape test mandatory masih SKIP pada Windows tanpa privilege, sehingga filesystem security belum dapat PASS penuh.

## Rollback
Tidak mengaktifkan tool baru atau mengganti registry. Perubahan exposure transport membutuhkan scope, backup, approval risiko, audit dan regression. Dokumen ini dapat dihapus selektif jika perlu; existing contracts tetap dipertahankan.

## Evidence dan change control

Source yang disebut adalah implementation reference. Bukti historis: `reports/NUSANTARA-V1-RECOVERY-REPORT-2026-10-06.md`; hasil closure: `reports/NUSANTARA-V1-FINAL-CLOSURE-REPORT-2026-10-06.md`. Kontrak baru tidak mengubah source, test, konfigurasi atau database. Risiko: interpretasi dokumen melebihi evidence; karena itu gaps tetap eksplisit. Rollback dokumen: hapus hanya file baru ini setelah review, pertahankan kontrak sebelumnya.
